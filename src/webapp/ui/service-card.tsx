import { Service, ServiceRelease } from '#/app/api/resources/cluster';
import Link from 'next/link';

export const ServiceCard = ({
  service,
}: {
  service?: Service;
}) => {
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <span className='font-bold'>Docker Image:</span> {service?.docker_image_name}<br></br>
      <span className='font-bold'>Detection Algorithm:</span> {service?.algo_name}<br></br>
      <span className='font-bold'>Reporting Measures:</span> {service?.passive_measure ? `Passive` : `Active`}
    </div>
  );
};
