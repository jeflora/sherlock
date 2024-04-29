export type ServiceRelease = {
  mri_cd_component: number,
  version: string,
  image_tag: string,
  docker_image_sha: string,
  active: boolean,
};

export type Service = {
  name: string,
  docker_image_name: string,
  algo_name: string,
  algo_params: {}
  passive_measure: boolean,
  versions?: [ServiceRelease],
};

export type Application = {
  app_name: string,
  namespace: string,
  monitor_filters: string,
  services?: [Service],
};

export type Cluster = {
  _id: string,
  hostname: string,
  name: string,
  ca_file: string,
  port: number,
  node_taints: [string],
  applications?: [Application],
};