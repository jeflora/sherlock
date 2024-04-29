import { getK8sResources } from '#/app/api/resources/getResources';

export default async function Page({
  params,
}: {
  params: { clusterSlug: string };
}) {
  const nodes = await getK8sResources({cluster_name: params.clusterSlug, resource_type: 'nodes'});
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {nodes.map((item) => {
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
