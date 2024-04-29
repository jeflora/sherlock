import React from 'react';
import { TabGroup } from '#/ui/tab-group';
import { getClusterAppDetails, getClusterAppServicesList } from '#/app//api/resources/getClusterResources';
import { Service } from '#/app/api/resources/cluster';
import { ApplicationCard } from '#/ui/application-card';

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { clusterSlug: string, appSlug: string };
}) {
  const app_details = await getClusterAppDetails({ cluster_name: params.clusterSlug, app_name: params.appSlug });
  const services = await getClusterAppServicesList({ cluster_name: params.clusterSlug, app_name: params.appSlug });
  return (
    <div className="space-y-9">
      <ApplicationCard application={app_details} />
      <div className="flex justify-between">
        <TabGroup
          path={`/clusters/${params.clusterSlug}/${params.appSlug}`}
          items={[
            {
              text: 'All Services',
            },
            ...services?.map((x: Service) => ({
              text: x.name,
              slug: x.name,
            })),
          ]}
        />
      </div>
      <div>{children}</div>
    </div>
  );
}
