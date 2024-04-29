import Link from 'next/link';
import { getClustersAvailable } from '../api/resources/getClusterResources';

export default async function Page() {
  const clusters = await getClustersAvailable();
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <p>For details about µSherlock see the <a href='https://github.com/jeflora/sherlock' target='_blank'>GitHub repo</a> or the <a href='https://jeflora.github.io/sherlock/' target='_blank'>website</a>.</p>
    </div>
  );
}
