import React from 'react';
import { TabGroup } from '#/ui/tab-group';
import { getClustersAvailable } from '../api/resources/getClusterResources';

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const clusters = await getClustersAvailable();
  return (
    <div className="space-y-9">
      <h1 className="text-xl font-bold">µSherlock Clusters</h1>
      <div className="flex justify-between">
        <TabGroup
          path="/clusters"
          items={[
            {
              text: 'All Clusters',
            },
            ...clusters.map((x) => ({
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
