import React from 'react';
import { getClusterAppServiceDetails } from '#/app//api/resources/getClusterResources';
import { Boundary } from '#/ui/boundary';
import { ServiceCard } from '#/ui/service-card';

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { clusterSlug: string, appSlug: string, serviceSlug: string };
}) {
  const service = await getClusterAppServiceDetails({ cluster_name: params.clusterSlug, app_name: params.appSlug, service_name: params.serviceSlug });
  return (
    <Boundary>
      <div className="space-y-9">
        <ServiceCard service={service} />
        <div>{children}</div>
      </div>
    </Boundary>
  );
}
