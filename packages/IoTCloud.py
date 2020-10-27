import time
import requests

from multiprocessing import Process, Value, Array, active_children
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter
from packages import Shared




logger = ConfigModule.getLogger()
net_logger = ConfigModule.getNETLogger()

class UbidotsConnect:
    process_name = 'IoT_Process'
    tc = TempConverter()
    net_logger_flag = False

    # Ubidots indicator custom color logic; we set ranges of values that point to a color
    # range is 0-100:
    # 0 - 10    = OFF
    # 11 - 20   = Compressor
    # 21 - 40   = LO heater
    # 41 - 60   = HI heater
    # 61 - 80   = LO + HI heater
    # 81 - 100  = WARNING

    def map_out(self, lo_heater_state, hi_heater_state, compressor_state):
        view_code = f"{lo_heater_state}{hi_heater_state}{compressor_state}"
        state_map = {
                        '000': 0,
                        '001': 15,
                        '010': 50,
                        '011': 100,
                        '100': 30,
                        '101': 100,
                        '110': 70,
                        '111': 100
                     }
        return state_map.get(view_code)


    def post_request(self, temp_meas, temp_ext, temp_target, remaining_time, duration, lo_heater, hi_heater, compressor, program_details, server_status, power_status):
        while(True):
            try:
                # Creates the headers for the HTTP requests
                # http://industrial.api.ubidots.com/api/v1.6/devices/Dough-O
                url = f"{ConfigModule.ubidots_url}{ConfigModule.ubidots_api}{ConfigModule.ubidots_device_label}"
                headers = {"X-Auth-Token": ConfigModule.ubidots_token, "Content-Type": "application/json"}


                prgm_details = str(program_details.value.decode())
                rem_time = str(remaining_time.value.decode())
                out_state = self.map_out(lo_heater.value, hi_heater.value, compressor.value)

                payload = {
                            ConfigModule.ub_var_temp_int: temp_meas.value,
                            ConfigModule.ub_var_temp_ext: temp_ext.value,
                            ConfigModule.ub_var_temp_target: temp_target.value,
                            ConfigModule.ub_var_duration: duration.value,
                            ConfigModule.ub_var_out_state: out_state,
                            ConfigModule.ub_var_power_status: power_status.value,
                            ConfigModule.ub_var_prgm_details: {"value": 1, "context": {"prgm_details": prgm_details}},
                            ConfigModule.ub_var_remaining_time: {"value": 1, "context": {"time_fmt": rem_time}}
                        }


                # Makes the HTTP requests
                server_status.value = 400
                attempts = 0
                while server_status.value <= 400 and attempts <= 5:

                    req = requests.post(url=url, headers=headers, json=payload)
                    server_status.value = req.status_code
                    attempts += 1


                    logger.info(f"PAYLOAD: {payload}")
                    logger.info(f"UBIDOTS RESPONSE: {server_status.value}")

                # Processes results
                if server_status.value >= 400:
                    logger.error("[ERROR] Could not send data after 5 attempts, please check \
                        your token credentials and internet connection")
                    if self.net_logger_flag == False:
                        net_logger.error(f"ERROR: {server_status.value} WHILE CONNECTING TO UBIDOTS")
                        self.net_logger_flag = True
                else:
                    logger.info("[INFO] UBIDOTS: request made properly!")
                    self.net_logger_flag = True

                

            except Exception as ex:
                logger.error(f"[ERR] UBIDOTS SERVER STATUS: {server_status.value}")
                net_logger.error(f"ERROR: {ex} WHILE CONNECTING TO UBIDOTS")
                logger.error(f"Exception in IoTCloud package: {ex}")
                raise
            
            finally:
                time.sleep(20)     

    # not used
    def get_var(self,device, variable):
        try:
            #url = "http://industrial.api.ubidots.com/"
            #url = url + \
                #"api/v1.6/devices/{0}/{1}/".format(device, variable)
            url = f"{ConfigModule.ubidots_url}{ConfigModule.ubidots_api}{device}/{variable}/"
            headers = {"X-Auth-Token": ConfigModule.ubidots_token, "Content-Type": "application/json"}
            req = requests.get(url=url, headers=headers)
            return req.json()['last_value']['value']
        except:
            pass



    def start_iot_communication(self, enable):
        if enable == True:
            IoT_process = Process(target=self.post_request,
                                name = self.process_name,
                                args= (
                                        Shared.TEMP_MEAS,
                                        Shared.TEMP_EXT,
                                        Shared.ACTUAL_TEMP_TARGET,
                                        Shared.REMAINING_TIME_FMT,
                                        Shared.MP_ACTUAL_PHASE_DURATION,
                                        Shared.LO_HEATER_STATE,
                                        Shared.HI_HEATER_STATE,
                                        Shared.COMPRESSOR_STATE,
                                        Shared.PROGRAM_DETAILS,
                                        Shared.SERVER_STATUS,
                                        Shared.POWER_STATUS_CODE
                                    )
                                )
            IoT_process.start()

    def stop_iot_communication(self):
        for p in active_children():
            if p.name == self.process_name:
                logger.info(f"Terminating active processes: {p.name}")
                p.terminate()

    def restart_iot_communication(self):
        for p in active_children():
            if p.name == self.process_name:
                logger.info(f"Terminating active processes: {p.name}")
                p.terminate()
        self.start_iot_communication(ConfigModule.cloud)
