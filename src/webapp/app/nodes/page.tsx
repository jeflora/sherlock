import Link from 'next/link';
import { getClustersAvailable } from '../api/resources/getClusterResources';

export default async function Page() {
  const clusters = await getClustersAvailable();
  return (
    <div className="prose prose-sm prose-invert max-w-none">

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {clusters.map((item) => {
          return (
            <Link
              href={`/nodes/${item.name}`}
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
