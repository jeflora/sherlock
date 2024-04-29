import {
  getNamespaceAvailableResources,
} from '#/app/api/resources/getResources';
import { TabGroup } from '#/ui/tab-group';

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { clusterSlug: string, namespaceSlug: string };
}) {
  const resource_types = await getNamespaceAvailableResources();

  return (
    <div className="space-y-9">
      <div className="flex justify-between">
        <TabGroup
          path={`/namespaces/${params.clusterSlug}/${params.namespaceSlug}`}
          items={[
            {
              text: 'Home',
            },
            ...resource_types.map((x) => ({
              text: x,
              slug: x,
            })),
          ]}
        />
      </div>

      <div>{children}</div>
    </div>
  );
}
