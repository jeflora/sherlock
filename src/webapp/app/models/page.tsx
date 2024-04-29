import { DetectionModelCard } from '#/ui/detection-model-card';
import { getDetectionModels } from '../api/resources/getDetectionModels';

export default async function Page() {
  const models = await getDetectionModels();
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <h1 className="text-xl font-bold pb-4">µSherlock Detection Models</h1>

      <div className="grid grid-cols-2 gap-5 lg:grid-cols-3">
        {models.map((item) => {
          return (
            <DetectionModelCard model={item}/>
          );
        })}
      </div>
    </div>
  );
}
