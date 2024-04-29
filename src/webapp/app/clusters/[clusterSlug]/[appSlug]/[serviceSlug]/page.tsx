import {
  getClusterAppServiceDetails
} from '#/app/api/resources/getClusterResources';
import { ServiceReleaseCard } from '#/ui/service-release-card';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string, appSlug: string, serviceSlug: string };
}) {
  const service_details = await getClusterAppServiceDetails({ cluster_name: params.clusterSlug, app_name: params.appSlug, service_name: params.serviceSlug });
  return (
    <ServiceReleaseCard service={service_details} />
  );
}
