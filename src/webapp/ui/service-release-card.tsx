import { Service, ServiceRelease } from '#/app/api/resources/cluster';
import Link from 'next/link';

export const ServiceReleaseCard = ({
  service,
}: {
  service?: Service;
}) => {
  return (
    <div className="prose prose-sm prose-invert max-w-none">
      <p className="text-xl font-bold">Service Releases</p>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {service?.versions ? service.versions.map((item: ServiceRelease) => {
          return (
            <div
              key={item.version}
              className={"group block space-y-1.5 rounded-lg px-5 py-3  " + (item.active ? "bg-gray-900" : "bg-gray-700")}
            >
              <div className="font-medium text-xl underline font-bold text-gray-200 group-hover:text-gray-50 pb-4 capitalize">
                {item.version}
              </div>
              <div className="font-medium text-gray-200 group-hover:text-gray-50 capitalize">
                Docker Image Tag: {item.image_tag}<br></br>
                Docker Image Hash: {item.docker_image_sha.substring(7, 19)}<br></br>
                MRI Source Code: {item.mri_cd_component}
              </div>
            </div>
          );
        }) : null}
      </div>
    </div>
  );
};
