#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import List
from sqlalchemy.sql.expression import update, select
from datetime import datetime

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from wattrex_battery_cycler_datatypes.comm_data import CommDataCuC, CommDataHeartbeatC,\
    CommDataDeviceC

#######################          PROJECT IMPORTS         #######################
from wattrex_driver_db import DrvDbDetectedDeviceC, DrvDbSqlEngineC, DrvDbTypeE, DrvDbComputationalUnitC,\
    DrvDbAvailableCuE, DrvDbConnStatusE

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class DbFacadeC:

    def __init__(self) -> None:
        self.db : DrvDbSqlEngineC  = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file='.cred.db.yaml')
        self.last_cu_id = 0


    def get_last_cu_id(self) -> int:
        stmt = select(DrvDbComputationalUnitC.CUID).order_by(DrvDbComputationalUnitC.CUID.desc()).limit(1)
        res = self.db.session.execute(stmt).first()
        if res is not None:
            self.last_cu_id = res[0]

        return self.last_cu_id

    def get_available_cus(self) -> List[int]:
        stmt = select(DrvDbComputationalUnitC.CUID).filter(
            DrvDbComputationalUnitC.Available == DrvDbAvailableCuE.ON.value).\
                order_by(DrvDbComputationalUnitC.CUID.asc())
        res = self.db.session.execute(stmt).fetchall()
        cus = []
        for cu in res:
            cus.append(cu[0])
        return cus


    def register_cu(self, cu_info : CommDataCuC) -> None:
        log.info(f"Registering new CU: {cu_info}")
        self.last_cu_id += 1
        cu_db = DrvDbComputationalUnitC()
        cu_db.CUID = self.last_cu_id
        cu_db.HostName = cu_info.hostname
        cu_db.User = cu_info.user
        cu_db.IP = cu_info.ip
        cu_db.Port = cu_info.port
        cu_db.LastConnection = datetime.utcnow()
        cu_db.Available = DrvDbAvailableCuE.ON.value
        self.db.session.add(cu_db)


    def update_heartbeat(self, hb : CommDataHeartbeatC) -> None:
        stmt = update(DrvDbComputationalUnitC).where(DrvDbComputationalUnitC.CUID == hb.cu_id).values(LastConnection= hb.timestamp)
        self.db.session.execute(stmt)


    def update_devices(self, cu_id : int, devices : List[CommDataDeviceC]) -> None:
        for d in devices:
            db_dev = DrvDbDetectedDeviceC()
            db_dev.CUID = cu_id
            db_dev.CompDevID = d.comp_dev_id
            db_dev.SN = d.serial_number
            db_dev.LinkName = d.link_name
            db_dev.ConnStatus = DrvDbConnStatusE.CONNECTED.value
            self.db.session.add(db_dev)
            log.info(f"Adding device: {d.__dict__}")
            # TODO: add str for CommDataDeviceC
            # TODO: use add or update: depending if exists or not

    def track_avail_cu(self) -> None:
        pass
        # TODO: implement this function


    def commit(self) -> None:
        self.db.commit_changes()

#######################            FUNCTIONS             #######################