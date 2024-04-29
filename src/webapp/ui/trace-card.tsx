import { Trace } from '#/app/api/resources/trace';
import Link from 'next/link';
import Button from './button';

import { FaRegTrashCan } from "react-icons/fa6";


export const TraceCard = ({
  trace,
}: {
  trace?: Trace;
}) => {
  return (
    <div
      key={trace?.file_id}
      className="group block space-y-1.5 rounded-lg bg-gray-900 px-5 py-3 "
    >
      <div className="font-medium text-gray-200 group-hover:text-gray-50">
        <div className='underline pb-4'>{trace?.file_name}</div>
        Application: <Link className='hover:bg-gray-800' href={`/clusters/${trace?.cluster_name}/${trace?.app_name}`}>{trace?.app_name}</Link><br></br>
        {trace?.zip_bytes ? `Zip size: ${trace?.zip_bytes}b` : ``}
        {trace?.zip_bytes ? <br></br> : null}
      </div>
      <Button kind='delete'>
        <FaRegTrashCan />
      </Button>
    </div>
  );
};
