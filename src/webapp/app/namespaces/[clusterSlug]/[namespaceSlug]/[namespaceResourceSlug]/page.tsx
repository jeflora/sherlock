import { getNamespaceResources } from '#/app/api/resources/getResources';
import Link from 'next/link';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string; namespaceSlug: string; namespaceResourceSlug: string };
}) {
  const resources = await getNamespaceResources({
    cluster_name: params.clusterSlug,
    namespace: params.namespaceSlug,
    resource_type: params.namespaceResourceSlug,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-medium text-gray-400/80 capitalize">
        {params.namespaceResourceSlug}
      </h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {resources.map((item) => {
          return (
            <div
              key={item.name}
              className="group block space-y-1.5 rounded-lg bg-gray-900 px-5 py-3 "
            >
              <div className="font-medium text-gray-200 group-hover:text-gray-50">
                {item.name}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
