import { getK8sResources } from '#/app/api/resources/getResources';
import { TabGroup } from '#/ui/tab-group';
import React from 'react';

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { clusterSlug: string };
}) {
  const namespaces = await getK8sResources({ cluster_name: params.clusterSlug, resource_type: 'namespaces' });
  return (
    <div className="space-y-9">
      <h1 className="text-xl font-bold">Kubernetes Namespaces</h1>
      <div className="flex justify-between">
        <TabGroup
          path={`/namespaces/${params.clusterSlug}`}
          items={[
            {
              text: 'Home',
            },
            ...namespaces.map((x) => ({
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
