import { notFound } from 'next/navigation';
import type { Resource } from './resource';

// `server-only` guarantees any modules that import code in file
// will never run on the client. Even though this particular api
// doesn't currently use sensitive environment variables, it's
// good practise to add `server-only` preemptively.
import 'server-only';

export async function getK8sResources({
  cluster_name,
  resource_type,
  name,
}: {
  cluster_name: string;
  resource_type: string;
  name?: string;
}) {
  const res = await fetch(
    `${process.env.API_URL}/cluster/${cluster_name}/${resource_type}/${name ? `?name=${name}` : ''}`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    // Render the closest `error.js` Error Boundary
    throw new Error('Something went wrong!');
  }

  const resources = (await res.json()) as Resource[];

  if (resources.length === 0) {
    // Render the closest `not-found.js` Error Boundary
    notFound();
  }

  return resources;
}

export async function getNamespaceResources({
  cluster_name,
  namespace,
  resource_type,
}: {
  cluster_name: string;
  namespace: string;
  resource_type: string;
}) {
  const res = await fetch(
    `${process.env.API_URL}/cluster/${cluster_name}/${namespace}/${resource_type}`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    // Render the closest `error.js` Error Boundary
    throw new Error('Something went wrong!');
  }

  const resources = (await res.json()) as Resource[];

  if (resources.length === 0) {
    // Render the closest `not-found.js` Error Boundary
    notFound();
  }

  return resources;
}

export async function getNamespaceAvailableResources({
  resource_type,
}: {
  resource_type?: string;
} = {}) {
  const res = await fetch(
    `${process.env.API_URL}/cluster/namespaces/resources/${resource_type ? `?type=${resource_type}` : ''
    }`,
    { next: { revalidate: 10 } },
  );

  if (!res.ok) {
    // Render the closest `error.js` Error Boundary
    throw new Error('Something went wrong!');
  }

  const resources = (await res.json()) as string[];

  if (resources.length === 0) {
    // Render the closest `not-found.js` Error Boundary
    notFound();
  }

  return resources;
}
