import { DetectionModel } from '#/app/api/resources/detectionModel';
import Link from 'next/link';
import Button from './button';

import { FaRegTrashCan } from "react-icons/fa6";
import { SlMagnifier } from "react-icons/sl";



export const DetectionModelCard = ({
  model,
}: {
  model?: DetectionModel;
}) => {
  return (
    <div
      key={model?.model_id}
      className="group block space-y-1.5 rounded-lg bg-gray-900 px-5 py-3 "
    >
      <div className="font-medium text-gray-200 group-hover:text-gray-50">
        <div className='underline pb-4'>{model?.model_id}</div>
        Application: <Link className='hover:bg-gray-800' href={`/applications/${model?.app_name}`}>{model?.app_name}</Link><br></br>
        Service: <Link className='hover:bg-gray-800' href={`/services/${model?.service}`}>{model?.service}</Link><br></br>
        Algorithm: {model?.name}<br></br>
        Docker Image: {model?.docker_image}<br></br>
      </div>

      <Button kind='delete'>
        <FaRegTrashCan />
      </Button>

      <Button kind='detection'>
        <SlMagnifier />
      </Button>
    
    </div>
  );
};
