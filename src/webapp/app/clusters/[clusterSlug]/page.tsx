import Link from 'next/link';
import { getClusterApplicationsList } from '#/app/api/resources/getClusterResources';
import { Resource } from '#/app/api/resources/resource';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string };
}) {
  const apps = await getClusterApplicationsList({ cluster_name: params.clusterSlug });
  return (
    <div className="prose prose-sm prose-invert max-w-none">

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {apps.map((item: Resource) => {
          return (
            <Link
              href={`/clusters/${params.clusterSlug}/${item.name}`}
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
