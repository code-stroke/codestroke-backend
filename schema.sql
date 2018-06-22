CREATE DATABASE IF NOT EXISTS `codestroke$codestroke`;
USE `codestroke$codestroke`;

CREATE TABLE IF NOT EXISTS `cases` (
  `case_id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `dob` date NOT NULL,
  `address` text DEFAULT NULL,
  `gender` tinyint DEFAULT NULL,
  `last_well` datetime DEFAULT NULL,
  `nok` varchar(40) DEFAULT NULL,
  `nok_phone` varchar(16) DEFAULT NULL,
  `medicare_no` varchar(12) DEFAULT NULL,
  `status` tinyint DEFAULT 0,
  `status_time` datetime DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `case_hospitals` (
  `case_id` int NOT NULL,
  `hospital_id` int NOT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `case_histories` (
  `case_id` int NOT NULL PRIMARY KEY,
  `pmhx` text DEFAULT NULL,
  `meds` text DEFAULT NULL,
  `anticoags` bool DEFAULT NULL,
  `anticoags_last_dose` datetime DEFAULT NULL,
  `hopc` text DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `last_meal` datetime DEFAULT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `case_assessments` (
  `case_id` int NOT NULL PRIMARY KEY,
  `facial_droop` bool DEFAULT NULL,
  `arm_drift` bool DEFAULT NULL,
  `weak_grip` bool DEFAULT NULL,
  `speech_difficulty` bool DEFAULT NULL,
  `bp_systolic` int DEFAULT NULL,
  `bp_diastolic` int DEFAULT NULL,
  `heart_rate` int DEFAULT NULL,
  `heart_rhythm` bool DEFAULT NULL,
  `rr` int DEFAULT NULL,
  `o2sats` int DEFAULT NULL,
  `temp` int DEFAULT NULL,
  `gcs` int DEFAULT NULL,
  `blood_glucose` int DEFAULT NULL,
  `facial_palsy_race` tinyint DEFAULT NULL,
  `arm_motor_impair` tinyint DEFAULT NULL,
  `leg_motor_impair` tinyint DEFAULT NULL,
  `head_gaze_deviate` tinyint DEFAULT NULL,
  `hemiparesis` bool DEFAULT NULL,
  `cannula` bool DEFAULT NULL,
  `conscious_level` tinyint DEFAULT NULL,
  `month_age` tinyint DEFAULT NULL,
  `blink_squeeze` tinyint DEFAULT NULL,
  `horizontal_gaze` tinyint DEFAULT NULL,
  `visual_fields` tinyint DEFAULT NULL,
  `facial_palsy_nihss` tinyint DEFAULT NULL,
  `left_arm_drift` tinyint DEFAULT NULL,
  `right_arm_drift` tinyint DEFAULT NULL,
  `left_leg_drift` tinyint DEFAULT NULL,
  `right_leg_drift` tinyint DEFAULT NULL,
  `limb_ataxia` tinyint DEFAULT NULL,
  `sensation` tinyint DEFAULT NULL,
  `aphasia` tinyint DEFAULT NULL,
  `dysarthria` tinyint DEFAULT NULL,
  `neglect` tinyint DEFAULT NULL,
  `rankin_conscious` tinyint DEFAULT NULL
  `likely_lvo` bool DEFAULT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `case_eds` (
  `case_id` int NOT NULL PRIMARY KEY,
  `location` VARCHAR(30) DEFAULT NULL,
  `registered` bool DEFAULT 0,
  `triaged` bool DEFAULT 0,
  `primary_survey` bool DEFAULT 0,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `case_radiologies` (
  `case_id` int NOT NULL PRIMARY KEY,
  `ct1` bool DEFAULT 0,
  `ct2` bool DEFAULT 0,
  `ct3` bool DEFAULT 0,
  `arrived_to_ct` bool DEFAULT 0,
  `ct_complete` bool DEFAULT 0,
  `ich_found` bool DEFAULT NULL,
  `do_cta_ctp` bool DEFAULT NULL,
  `cta_ctp_complete` bool DEFAULT 0,
  `large_vessel_occlusion` bool DEFAULT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `case_managements` (
  `case_id` int NOT NULL PRIMARY KEY,
  `thrombolysis` bool DEFAULT NULL,
  `new_trauma_haemorrhage` bool DEFAULT NULL,
  `uncontrolled_htn` bool DEFAULT NULL,
  `history_ich` bool DEFAULT NULL,
  `known_intracranial` bool DEFAULT NULL,
  `active_bleed` bool DEFAULT NULL,
  `endocarditis` bool DEFAULT NULL,
  `bleeding_diathesis` bool DEFAULT NULL,
  `abnormal_blood_glucose` bool DEFAULT NULL,
  `rapidly_improving` bool DEFAULT NULL,
  `recent_trauma_surgery` bool DEFAULT NULL,
  `recent_active_bleed` bool DEFAULT NULL,
  `seizure_onset` bool DEFAULT NULL,
  `recent_arterial_puncture` bool DEFAULT NULL,
  `recent_lumbar_puncture` bool DEFAULT NULL,
  `post_acs_pericarditis` bool DEFAULT NULL,
  `pregnant` bool DEFAULT NULL,
  `thrombolysis_time_given` datetime DEFAULT NULL,
  `ecr` bool DEFAULT NULL,
  `surgical_rx` bool DEFAULT NULL,
  `conservative_rx` bool DEFAULT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS `clinicians` (
  `id` int NOT NULL PRIMARY KEY,
  `first_name` varchar(30) DEFAULT NULL,
  `last_name` varchar(30) DEFAULT NULL,
  `username` varchar(20) NOT NULL,
  `pwhash` text NOT NULL,
  `hospital_id` int,
  `role` int,
  `creation_date` date,
  `email` varchar(40)
);

CREATE TABLE IF NOT EXISTS `hospitals` (
  `id` int NOT NULL PRIMARY KEY,
  `name` varchar(30) NOT NULL,
  `city` varchar(30),
  `state` varchar(5),
  `postcode` varchar(30),
  `latitude` text,
  `longitude` text
);
