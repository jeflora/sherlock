import { getTraces } from '../api/resources/getTraces';
import { TraceCard } from '#/ui/trace-card';

export default async function Page() {
  const traces = await getTraces();
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <h1 className="text-xl font-bold pb-4">µSherlock System Call Traces</h1>

      <div className="grid grid-cols-2 gap-5 lg:grid-cols-3">
        {traces.map((item) => {
          return (
            <TraceCard trace={item}/>
          );
        })}
      </div>
    </div>
  );
}
