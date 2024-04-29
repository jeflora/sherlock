import React from 'react';
import { TabGroup } from '#/ui/tab-group';
import { getClusterApplicationsList } from '#/app//api/resources/getClusterResources';
import { Resource } from '#/app/api/resources/resource';

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { clusterSlug: string };
}) {
  const apps = await getClusterApplicationsList({ cluster_name: params.clusterSlug })
  return (
    <div className="space-y-9">
      <div className="flex justify-between">
        <TabGroup
          path={`/clusters/${params.clusterSlug}`}
          items={[
            {
              text: 'All Applications',
            },
            ...apps.map((x: Resource) => ({
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
