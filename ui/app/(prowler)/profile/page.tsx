import React, { Suspense } from "react";

import { getProfileInfo } from "@/actions/users/users";
import { ContentLayout } from "@/components/ui";
import { SkeletonUserInfo } from "@/components/users/profile";
import { UserInfo } from "@/components/users/profile/user-info";
import { UserProfileProps } from "@/types";

export default async function Profile() {
  return (
    <ContentLayout title="User Profile" icon="ci:users">
      <div className="min-h-screen">
        <div className="container mx-auto space-y-8 px-0 py-6">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 lg:col-span-3">
              <Suspense fallback={<SkeletonUserInfo />}>
                <SSRDataUser />
              </Suspense>
            </div>
          </div>
        </div>
      </div>
    </ContentLayout>
  );
}

const SSRDataUser = async () => {
  const userProfile: UserProfileProps = await getProfileInfo();

  return (
    <>
      <h3 className="mb-4 text-sm font-bold">User Info</h3>
      <UserInfo user={userProfile?.data} />
    </>
  );
};
