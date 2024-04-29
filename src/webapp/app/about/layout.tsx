import React from 'react';
import { TabGroup } from '#/ui/tab-group';
import { getClustersAvailable } from '../api/resources/getClusterResources';

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const clusters = await getClustersAvailable();
  return (
    <div className="space-y-9">
      {children}
    </div>
  );
}