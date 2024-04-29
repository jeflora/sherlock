export type Trace = {
    file_id: number,
    app_name: string,
    cluster_name: string,
    file_name: string,
    begin_date: Date,
    end_date: Date,
    text_bytes: number,
    zip_bytes: number,
    created_at: Date
};