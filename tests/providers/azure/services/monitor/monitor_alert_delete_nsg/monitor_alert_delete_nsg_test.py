from unittest import mock

from azure.mgmt.monitor.models import AlertRuleAnyOfOrLeafCondition

from tests.providers.azure.azure_fixtures import (
    AZURE_SUBSCRIPTION_ID,
    set_mocked_azure_provider,
)


class Test_monitor_alert_delete_nsg:
    def test_monitor_alert_delete_nsg_no_subscriptions(self):
        monitor_client = mock.MagicMock()
        monitor_client.alert_rules = {}
        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=set_mocked_azure_provider(),
            ),
            mock.patch(
                "prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg.monitor_client",
                new=monitor_client,
            ),
        ):
            from prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg import (
                monitor_alert_delete_nsg,
            )

            check = monitor_alert_delete_nsg()
            result = check.execute()
            assert len(result) == 0

    def test_no_alert_rules(self):
        monitor_client = mock.MagicMock()
        monitor_client.alert_rules = {AZURE_SUBSCRIPTION_ID: []}
        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=set_mocked_azure_provider(),
            ),
            mock.patch(
                "prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg.monitor_client",
                new=monitor_client,
            ),
        ):
            from prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg import (
                monitor_alert_delete_nsg,
            )

            check = monitor_alert_delete_nsg()
            result = check.execute()
            assert len(result) == 1
            assert result[0].status == "FAIL"
            assert result[0].subscription == AZURE_SUBSCRIPTION_ID
            assert result[0].resource_name == "Monitor"
            assert result[0].resource_id == "Monitor"
            assert (
                result[0].status_extended
                == f"There is not an alert for deleting Network Security Groups in subscription {AZURE_SUBSCRIPTION_ID}."
            )

    def test_alert_rules_configured(self):
        monitor_client = mock.MagicMock

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=set_mocked_azure_provider(),
            ),
            mock.patch(
                "prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg.monitor_client",
                new=monitor_client,
            ),
        ):
            from prowler.providers.azure.services.monitor.monitor_alert_delete_nsg.monitor_alert_delete_nsg import (
                monitor_alert_delete_nsg,
            )
            from prowler.providers.azure.services.monitor.monitor_service import (
                AlertRule,
                AlertRuleAllOfCondition,
            )

            monitor_client.alert_rules = {
                AZURE_SUBSCRIPTION_ID: [
                    AlertRule(
                        id="id",
                        name="name",
                        condition=AlertRuleAllOfCondition(
                            all_of=[
                                AlertRuleAnyOfOrLeafCondition(),
                                AlertRuleAnyOfOrLeafCondition(
                                    equals="Microsoft.Network/networkSecurityGroups/delete",
                                    field="operationName",
                                ),
                            ]
                        ),
                        enabled=False,
                        description="description",
                    ),
                    AlertRule(
                        id="id2",
                        name="name2",
                        condition=AlertRuleAllOfCondition(
                            all_of=[
                                AlertRuleAnyOfOrLeafCondition(),
                                AlertRuleAnyOfOrLeafCondition(
                                    equals="Microsoft.Network/networkSecurityGroups/delete",
                                    field="operationName",
                                ),
                            ]
                        ),
                        enabled=True,
                        description="description2",
                    ),
                ]
            }
            check = monitor_alert_delete_nsg()
            result = check.execute()
            assert len(result) == 1
            assert result[0].status == "PASS"
            assert result[0].subscription == AZURE_SUBSCRIPTION_ID
            assert result[0].resource_name == "name2"
            assert result[0].resource_id == "id2"
            assert (
                result[0].status_extended
                == f"There is an alert configured for deleting Network Security Groups in subscription {AZURE_SUBSCRIPTION_ID}."
            )
