"use client";

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Chart as ChartJS, defaults } from "chart.js/auto";
import { Line } from "react-chartjs-2";
import 'chartjs-adapter-moment';
import { Alarm } from '../api/resources/alarm';

defaults.maintainAspectRatio = true;
defaults.responsive = true;

//defaults.plugins.title.display = true;
//defaults.plugins.title.align = "start";
//defaults.plugins.title.font.size = 20;
//defaults.plugins.title.color = "white";

export default function Page() {
  // TODO: This should not be hardcoded
  const host = "http://10.3.3.223";
  // DropDowns
  const [clusters, setClusters] = useState([] as string[]);
  const [apps, setApps] = useState([] as string[]);
  const [services, setServices] = useState([] as string[]);
  const [selectedCluster, setSelectedCluster] = useState('');
  const [selectedApp, setSelectedApp] = useState('');
  const [selectedService, setSelectedService] = useState('');
  //Plots
  const [data, setData] = useState([] as Alarm[]);

  useEffect(() => {
    axios.get(`${host}/clusters/names`)
      .then(response => {
        setClusters(response.data);
      })
      .catch(error => {
        console.log(error);
      });
  }, []);

  useEffect(() => {
    if (selectedCluster) {
      axios.get(`${host}/automation/${selectedCluster}/list/apps/names`)
        .then(response => {
          setApps(response.data);
        })
        .catch(error => {
          console.log(error);
        });
    }
  }, [selectedCluster]);

  useEffect(() => {
    if (selectedCluster && selectedApp) {
      axios.get(`${host}/automation/${selectedCluster}/${selectedApp}/list/services/names`)
        .then(response => {
          setServices(response.data);
        })
        .catch(error => {
          console.log(error);
        });
    }
  }, [selectedCluster, selectedApp]);

  const handleClustersChange = (event: { target: { value: string; }; }) => {
    setSelectedCluster(event.target.value);
    setSelectedApp('');
    setSelectedService('');
    setData([]);
  };

  const handleAppsChange = (event: { target: { value: string; }; }) => {
    setSelectedApp(event.target.value);
    setSelectedService('');
    setData([]);
  };

  const handleServicesChange = (event: { target: { value: string; }; }) => {
    setSelectedService(event.target.value);
    setData([]);
  };
  const classes = "mx-10 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500";


  // Plots

  useEffect(() => {
    const fetchData = () => {
      var getParams: any = {}

      if (selectedApp) {
        getParams.app_name = selectedApp;
      }

      if (selectedService) {
        getParams.service_name = selectedService;
      }

      if (data && data.length !== 0) {
        getParams.last_timestamp = data[data.length - 1].timestamp;
      }

      axios.get(`${host}/alarms/plot`, {
        params: getParams,
      })
        .then(response => {
          console.log(data.length);
          let tempData = null;
          if (data.length > 90) {
            tempData = data.slice(1);
          }
          setData(tempData ? tempData.concat(response.data) : data.concat(response.data));
        })
        .catch(error => {
          console.log(error);
        });
    };

    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);

  }, [selectedApp, selectedService, data]);
  return (
    <div className="space-y-9 h-full">
      <h1 className="text-xl font-bold">µSherlock Alarms</h1>
      {/* Dropdowns */}
      <div>
        <select className={classes} onChange={handleClustersChange} value={selectedCluster}>
          <option value="">Select Cluster</option>
          {clusters.map(item => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select className={classes} onChange={handleAppsChange} value={selectedApp}>
          <option value="">Select Application</option>
          {apps.map(item => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select className={classes} onChange={handleServicesChange} value={selectedService}>
          <option value="">Select Service</option>
          {services.map(item => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
      </div>
      {/* Plot */}
      <div className='my-5'>
        <div className="prose prose-sm prose-invert max-y-none max-w-none">
          <Line
            data={{
              labels: data.map((data) => data.timestamp),
              datasets: [
                {
                  label: "Alarms",
                  borderDash: [5, 5],
                  data: data.map((data) => data.alarms),
                  backgroundColor: "#FF3030",
                  borderColor: "#FF3030",
                  pointStyle: 'circle',
                  pointRadius: 5,
                  pointHoverRadius: 10
                },
              ],
            }}
            options={{
              responsive: true,
              elements: {
                line: {
                  tension: 0.5,
                },
              },
              scales: {
                y: {
                  min: 0,
                }
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}
