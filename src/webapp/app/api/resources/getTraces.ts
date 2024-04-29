import { notFound } from 'next/navigation';
import { Trace } from './trace';

import 'server-only';

export async function getTraces() {
    const res = await fetch(
        `${process.env.API_URL}/traces`,
        { next: { revalidate: 10 } },
    );

    if (!res.ok) {
        throw new Error('Something went wrong!');
    }

    const traces = (await res.json()) as Trace[];

    if (traces.length === 0) {
        notFound();
    }

    return traces;
}