import { Application, Service } from '#/app/api/resources/cluster';
import Link from 'next/link';

export const ApplicationCard = ({
  application,
}: {
  application?: Application;
}) => {
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <span className='font-bold'>Namespace:</span> {application?.namespace}<br></br>
      <span className='font-bold'>Monitor Filters:</span> {application?.monitor_filters}
    </div>
  );
};
