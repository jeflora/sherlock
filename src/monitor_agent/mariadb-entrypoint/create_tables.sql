create table if not exists data_traces (
	file_id	int not null auto_increment,
	app_name	varchar(100) not null,
	file_name	varchar(20) not null unique,
    begin_date datetime,
    end_date datetime,
	text_bytes int,
	zip_bytes int,
    created_at timestamp default current_timestamp,
	primary key( file_id )
);