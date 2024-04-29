import {
  getNamespaceAvailableResources,
  getK8sResources,
} from '#/app/api/resources/getResources';
import Link from 'next/link';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string, namespaceSlug: string };
}) {
  const namespace = await getK8sResources({
    cluster_name: params.clusterSlug,
    resource_type: 'namespaces',
    name: params.namespaceSlug,
  });
  const resource_types = await getNamespaceAvailableResources();
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      {/* <h1 className="text-xl font-bold">{params.namespaceSlug}</h1> */}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {resource_types.map((item) => {
          return (
            <Link
              href={`/namespaces/${params.clusterSlug}/${params.namespaceSlug}/${item}`}
              key={item}
              className="group block space-y-1.5 rounded-lg bg-gray-900 px-5 py-3 hover:bg-gray-800"
            >
              <div className="font-medium text-gray-200 group-hover:text-gray-50 capitalize">
                {item}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
