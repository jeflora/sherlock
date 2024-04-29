import { getK8sResources } from '#/app/api/resources/getResources';
import Link from 'next/link';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string };
}) {
  const namespaces = await getK8sResources({ cluster_name: params.clusterSlug ,resource_type: 'namespaces' });
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <h1 className="text-xl font-bold">Cluster Namespaces</h1>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {namespaces.map((item) => {
          return (
            <Link
              href={`/namespaces/${params.clusterSlug}/${item.name}`}
              key={item.name}
              className="group block space-y-1.5 rounded-lg bg-gray-900 px-5 py-3 hover:bg-gray-800"
            >
              <div className="font-medium text-gray-200 group-hover:text-gray-50">
                {item.name}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
