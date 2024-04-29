import { notFound } from 'next/navigation';
import type { Resource } from './resource';
import type { Cluster, Application, Service, ServiceRelease } from './cluster';
import { getCurrentApplication, getCurrentCluster } from '../state/storeClusterAndApp';

// `server-only` guarantees any modules that import code in file
// will never run on the client. Even though this particular api
// doesn't currently use sensitive environment variables, it's
// good practise to add `server-only` preemptively.
import 'server-only';

export async function getClustersAvailable({
  cluster_name,
}: {
  cluster_name?: string;
} = {}) {
  const res = await fetch(
    `${process.env.API_URL}/clusters${cluster_name ? `?cluster_name=${cluster_name}` : ''
    }`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    throw new Error('Something went wrong!');
  }

  const resources = (await res.json()) as Cluster[];

  if (resources.length === 0) {
    notFound();
  }

  return resources;
}

export async function getClusterApplicationsList({
  cluster_name,
} : {
  cluster_name : string
}) {

  const res = await fetch(
    `${process.env.API_URL}/automation/${cluster_name}/list/apps`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    throw new Error('Something went wrong!');
  }

  const applications = (await res.json()).map((app: string) => {
    return { name: app } as Resource
  });

  if (applications.length === 0) {
    notFound();
  }

  return applications;
}

export async function getClusterAppDetails({
  cluster_name,
  app_name,
}: {
  cluster_name : string;
  app_name : string;
}) {

  const res = await fetch(
    `${process.env.API_URL}/automation/${cluster_name}/${app_name}`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    throw new Error('Something went wrong!');
  }

  const application = (await res.json()) as Application;

  if (!application) {
    notFound();
  }

  return application;
}

export async function getClusterAppServicesList({
  cluster_name,
  app_name,
}: {
  cluster_name: string;
  app_name: string;
}) {

  const res = await fetch(
    `${process.env.API_URL}/automation/${cluster_name}/${app_name}/list/services`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    throw new Error('Something went wrong!');
  }

  const services = (await res.json()) as Service[];

  if (services.length === 0) {
    notFound();
  }

  return services;
}

export async function getClusterAppServiceDetails({
  cluster_name,
  app_name,
  service_name,
}: {
  cluster_name: string;
  app_name: string;
  service_name: string;
}) {
  const services = await getClusterAppServicesList({cluster_name: cluster_name, app_name: app_name});

  if (services.length === 0) {
    notFound();
  }

  return services.find(service => service.name === service_name)
}

export async function getClusterAppServicesReleases({
  cluster_name,
  app_name,
  service_name,
}: {
  cluster_name: string;
  app_name: string;
  service_name: string;
}) {

  const res = await fetch(
    `${process.env.API_URL}/automation/${cluster_name}/${app_name}/${service_name}/list/releases`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    throw new Error('Something went wrong!');
  }

  const releases = (await res.json()) as ServiceRelease[];

  if (releases.length === 0) {
    notFound();
  }

  return releases;
}