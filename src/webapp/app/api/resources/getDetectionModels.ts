import { notFound } from 'next/navigation';
import { DetectionModel } from './detectionModel';

import 'server-only';

export async function getDetectionModels() {

    const res = await fetch(
        `${process.env.API_URL}/intrusion/models`,
        { next: { revalidate: 10 } },
    );

    if (!res.ok) {
        throw new Error('Something went wrong!');
    }

    const models = (await res.json()) as DetectionModel[];

    if (models.length === 0) {
        notFound();
    }

    return models;
}

export async function getDetectionModelDetails({
    model_id
} : {
    model_id: string
}) {

    const res = await fetch(
        `${process.env.API_URL}/intrusion/model/${model_id}`,
        { next: { revalidate: 10 } },
    );

    if (!res.ok) {
        throw new Error('Something went wrong!');
    }

    const model_details = (await res.json()) as DetectionModel;

    if (!model_details) {
        notFound();
    }

    return model_details;
}