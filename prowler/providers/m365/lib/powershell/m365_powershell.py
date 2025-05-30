import os

import msal

from prowler.lib.powershell.powershell import PowerShellSession
from prowler.providers.m365.exceptions.exceptions import (
    M365UserNotBelongingToTenantError,
)
from prowler.providers.m365.models import M365Credentials


class M365PowerShell(PowerShellSession):
    """
    Microsoft 365 specific PowerShell session management implementation.

    This class extends the base PowerShellSession to provide Microsoft 365 specific
    functionality, including authentication, Teams management, and Exchange Online
    operations.

    Features:
    - Microsoft 365 credential management
    - Teams client configuration
    - Exchange Online connectivity
    - Audit log configuration
    - Secure credential handling

    Attributes:
        credentials (M365Credentials): The Microsoft 365 credentials used for authentication.

    Note:
        This class requires the Microsoft Teams and Exchange Online PowerShell modules
        to be installed and available in the PowerShell environment.
    """

    def __init__(self, credentials: M365Credentials):
        """
        Initialize a Microsoft 365 PowerShell session.

        Sets up the PowerShell session and initializes the provided credentials
        for Microsoft 365 authentication.

        Args:
            credentials (M365Credentials): The Microsoft 365 credentials to use
                for authentication.
        """
        super().__init__()
        self.init_credential(credentials)

    def init_credential(self, credentials: M365Credentials) -> None:
        """
        Initialize PowerShell credential object for Microsoft 365 authentication.

        Sanitizes the username and password, then creates a PSCredential object
        in the PowerShell session for use with Microsoft 365 cmdlets.

        Args:
            credentials (M365Credentials): The credentials object containing
                username and password.

        Note:
            The credentials are sanitized to prevent command injection and
            stored securely in the PowerShell session.
        """
        # Sanitize user and password
        user = self.sanitize(credentials.user)
        passwd = self.sanitize(credentials.passwd)

        # Securely convert encrypted password to SecureString
        self.execute(f'$user = "{user}"')
        self.execute(f'$secureString = "{passwd}" | ConvertTo-SecureString')
        self.execute(
            "$credential = New-Object System.Management.Automation.PSCredential ($user, $secureString)"
        )

    def test_credentials(self, credentials: M365Credentials) -> bool:
        """
        Test Microsoft 365 credentials by attempting to authenticate against Entra ID.

        Args:
            credentials (M365Credentials): The credentials object containing
                username and password to test.

        Returns:
            bool: True if credentials are valid and authentication succeeds, False otherwise.
        """
        self.execute(
            f'$securePassword = "{credentials.passwd}" | ConvertTo-SecureString'
        )
        self.execute(
            f'$credential = New-Object System.Management.Automation.PSCredential("{credentials.user}", $securePassword)\n'
        )
        decrypted_password = self.execute(
            'Write-Output "$($credential.GetNetworkCredential().Password)"'
        )

        app = msal.ConfidentialClientApplication(
            client_id=credentials.client_id,
            client_credential=credentials.client_secret,
            authority=f"https://login.microsoftonline.com/{credentials.tenant_id}",
        )

        result = app.acquire_token_by_username_password(
            username=credentials.user,
            password=decrypted_password,  # Needs to be in plain text
            scopes=["https://graph.microsoft.com/.default"],
        )

        if result is None:
            return False

        if "access_token" not in result:
            return False

        # Validate user credentials belong to tenant
        user_domain = credentials.user.split("@")[1]
        if not credentials.provider_id.endswith(user_domain):
            raise M365UserNotBelongingToTenantError(
                file=os.path.basename(__file__),
                message="The provided M365 User does not belong to the specified tenant.",
            )

        return True

    def connect_microsoft_teams(self) -> dict:
        """
        Connect to Microsoft Teams Module PowerShell Module.

        Establishes a connection to Microsoft Teams using the initialized credentials.

        Returns:
            dict: Connection status information in JSON format.

        Note:
            This method requires the Microsoft Teams PowerShell module to be installed.
        """
        return self.execute("Connect-MicrosoftTeams -Credential $credential")

    def get_teams_settings(self) -> dict:
        """
        Get Teams Client Settings.

        Retrieves the current Microsoft Teams client configuration settings.

        Returns:
            dict: Teams client configuration settings in JSON format.

        Example:
            >>> get_teams_settings()
            {
                "AllowBox": true,
                "AllowDropBox": true,
                "AllowGoogleDrive": true
            }
        """
        return self.execute(
            "Get-CsTeamsClientConfiguration | ConvertTo-Json", json_parse=True
        )

    def get_global_meeting_policy(self) -> dict:
        """
        Get Teams Global Meeting Policy.

        Retrieves the current Microsoft Teams global meeting policy settings.

        Returns:
            dict: Teams global meeting policy settings in JSON format.

        Example:
            >>> get_global_meeting_policy()
            {
                "AllowAnonymousUsersToJoinMeeting": true
            }
        """
        return self.execute(
            "Get-CsTeamsMeetingPolicy -Identity Global | ConvertTo-Json",
            json_parse=True,
        )

    def get_user_settings(self) -> dict:
        """
        Get Teams User Settings.

        Retrieves the current Microsoft Teams user settings.

        Returns:
            dict: Teams user settings in JSON format.

        Example:
            >>> get_user_settings()
            {
                "AllowExternalAccess": true
            }
        """
        return self.execute(
            "Get-CsTenantFederationConfiguration | ConvertTo-Json", json_parse=True
        )

    def connect_exchange_online(self) -> dict:
        """
        Connect to Exchange Online PowerShell Module.

        Establishes a connection to Exchange Online using the initialized credentials.

        Returns:
            dict: Connection status information in JSON format.

        Note:
            This method requires the Exchange Online PowerShell module to be installed.
        """
        return self.execute("Connect-ExchangeOnline -Credential $credential")

    def get_audit_log_config(self) -> dict:
        """
        Get Purview Admin Audit Log Settings.

        Retrieves the current audit log configuration settings for Microsoft Purview.

        Returns:
            dict: Audit log configuration settings in JSON format.

        Example:
            >>> get_audit_log_config()
            {
                "UnifiedAuditLogIngestionEnabled": true
            }
        """
        return self.execute(
            "Get-AdminAuditLogConfig | Select-Object UnifiedAuditLogIngestionEnabled | ConvertTo-Json",
            json_parse=True,
        )

    def get_malware_filter_policy(self) -> dict:
        """
        Get Defender Malware Filter Policy.

        Retrieves the current Defender anti-malware filter policy settings.

        Returns:
            dict: Malware filter policy settings in JSON format.

        Example:
            >>> get_malware_filter_policy()
            {
                "EnableFileFilter": true,
                "Identity": "Default"
            }
        """
        return self.execute("Get-MalwareFilterPolicy | ConvertTo-Json", json_parse=True)

    def get_outbound_spam_filter_policy(self) -> dict:
        """
        Get Defender Outbound Spam Filter Policy.

        Retrieves the current Defender outbound spam filter policy settings.

        Returns:
            dict: Outbound spam filter policy settings in JSON format.

        Example:
            >>> get_outbound_spam_filter_policy()
            {
                "NotifyOutboundSpam": true,
                "BccSuspiciousOutboundMail": true,
                "BccSuspiciousOutboundAdditionalRecipients": [],
                "NotifyOutboundSpamRecipients": []
            }
        """
        return self.execute(
            "Get-HostedOutboundSpamFilterPolicy | ConvertTo-Json", json_parse=True
        )

    def get_outbound_spam_filter_rule(self) -> dict:
        """
        Get Defender Outbound Spam Filter Rule.

        Retrieves the current Defender outbound spam filter rule settings.

        Returns:
            dict: Outbound spam filter rule settings in JSON format.

        Example:
            >>> get_outbound_spam_filter_rule()
            {
                "State": "Enabled"
            }
        """
        return self.execute(
            "Get-HostedOutboundSpamFilterRule | ConvertTo-Json", json_parse=True
        )

    def get_antiphishing_policy(self) -> dict:
        """
        Get Defender Antiphishing Policy.

        Retrieves the current Defender anti-phishing policy settings.

        Returns:
            dict: Antiphishing policy settings in JSON format.

        Example:
            >>> get_antiphishing_policy()
            {
                "EnableSpoofIntelligence": true,
                "AuthenticationFailAction": "Quarantine",
                "DmarcRejectAction": "Quarantine",
                "DmarcQuarantineAction": "Quarantine",
                "EnableFirstContactSafetyTips": true,
                "EnableUnauthenticatedSender": true,
                "EnableViaTag": true,
                "HonorDmarcPolicy": true,
                "IsDefault": false
            }
        """
        return self.execute("Get-AntiPhishPolicy | ConvertTo-Json", json_parse=True)

    def get_antiphishing_rules(self) -> dict:
        """
        Get Defender Antiphishing Rules.

        Retrieves the current Defender anti-phishing rules.

        Returns:
            dict: Antiphishing rules in JSON format.

        Example:
            >>> get_antiphishing_rules()
            {
                "Name": "Rule1",
                "State": Enabled,
            }
        """
        return self.execute("Get-AntiPhishRule | ConvertTo-Json", json_parse=True)

    def get_organization_config(self) -> dict:
        """
        Get Exchange Online Organization Configuration.

        Retrieves the current Exchange Online organization configuration settings.

        Returns:
            dict: Organization configuration settings in JSON format.

        Example:
            >>> get_organization_config()
            {
                "Name": "MyOrganization",
                "Guid": "12345678-1234-1234-1234-123456789012"
                "AuditDisabled": false
            }
        """
        return self.execute("Get-OrganizationConfig | ConvertTo-Json", json_parse=True)

    def get_mailbox_audit_config(self) -> dict:
        """
        Get Exchange Online Mailbox Audit Configuration.

        Retrieves the current mailbox audit configuration settings for Exchange Online.

        Returns:
            dict: Mailbox audit configuration settings in JSON format.

        Example:
            >>> get_mailbox_audit_config()
            {
                "Name": "MyMailbox",
                "Id": "12345678-1234-1234-1234-123456789012",
                "AuditBypassEnabled": false
            }
        """
        return self.execute(
            "Get-MailboxAuditBypassAssociation | ConvertTo-Json", json_parse=True
        )

    def get_external_mail_config(self) -> dict:
        """
        Get Exchange Online External Mail Configuration.

        Retrieves the current external mail configuration settings for Exchange Online.

        Returns:
            dict: External mail configuration settings in JSON format.

        Example:
            >>> get_external_mail_config()
            {
                "Identity": "MyExternalMail",
                "ExternalMailTagEnabled": true
            }
        """
        return self.execute("Get-ExternalInOutlook | ConvertTo-Json", json_parse=True)

    def get_transport_rules(self) -> dict:
        """
        Get Exchange Online Transport Rules.

        Retrieves the current transport rules configured in Exchange Online.

        Returns:
            dict: Transport rules in JSON format.

        Example:
            >>> get_transport_rules()
            {
                "Name": "Rule1",
                "SetSCL": -1,
                "SenderDomainIs": ["example.com"]
            }
        """
        return self.execute("Get-TransportRule | ConvertTo-Json", json_parse=True)

    def get_connection_filter_policy(self) -> dict:
        """
        Get Exchange Online Connection Filter Policy.

        Retrieves the current connection filter policy settings for Exchange Online.

        Returns:
            dict: Connection filter policy settings in JSON format.

        Example:
            >>> get_connection_filter_policy()
            {
                "Identity": "Default",
                "IPAllowList": []"
            }
        """
        return self.execute(
            "Get-HostedConnectionFilterPolicy -Identity Default | ConvertTo-Json",
            json_parse=True,
        )

    def get_dkim_config(self) -> dict:
        """
        Get DKIM Signing Configuration.

        Retrieves the current DKIM signing configuration settings for Exchange Online.

        Returns:
            dict: DKIM signing configuration settings in JSON format.

        Example:
            >>> get_dkim_config()
            {
                "Id": "12345678-1234-1234-1234-123456789012",
                "Enabled": true
            }
        """
        return self.execute("Get-DkimSigningConfig | ConvertTo-Json", json_parse=True)

    def get_inbound_spam_filter_policy(self) -> dict:
        """
        Get Inbound Spam Filter Policy.

        Retrieves the current inbound spam filter policy settings for Exchange Online.

        Returns:
            dict: Inbound spam filter policy settings in JSON format.

        Example:
            >>> get_inbound_spam_filter_policy()
            {
                "Identity": "Default",
                "AllowedSenderDomains": "[]"
            }
        """
        return self.execute(
            "Get-HostedContentFilterPolicy | ConvertTo-Json", json_parse=True
        )
