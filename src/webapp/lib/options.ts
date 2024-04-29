export type Item = {
  name: string;
  slug: string;
  description?: string;
};

export const options: { name: string; items: Item[] }[] = [
  {
    name: 'Resources',
    items: [
      {
        name: 'Clusters',
        slug: 'clusters',
        description:
          'Manage µSherlock clusters',
      },
      {
        name: 'Traces',
        slug: 'traces',
        description: 'Manage µSherlock system call traces',
      },
      {
        name: 'Models',
        slug: 'models',
        description:
          'Manage µSherlock detection models',
      },
      {
        name: 'Alarms',
        slug: 'alarms',
        description: 'Manage µSherlock intrusion alarms',
      },
    ],
  },
  {
    name: 'Kubernetes',
    items: [
      {
        name: 'Nodes',
        slug: 'nodes',
        description: 'List the cluster nodes available',
      },
      {
        name: 'Namespaces',
        slug: 'namespaces',
        description: 'List the cluster namespaces',
      },
    ],
  },
  {
    name: 'Help',
    items: [
      {
        name: 'About µSherlock',
        slug: 'about',
        description:
          'Details about the architecture, components, and operation of µSherlock',
      },
    ],
  },
];
