CREATE DATABASE IF NOT EXISTS `codestroke`;
USE `codestroke`;

CREATE TABLE IF NOT EXISTS `cases` (
  `case_id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `dob` date NOT NULL,
  `address` text NOT NULL,
  `gender` varchar(1) NOT NULL,
  `last_well` datetime NOT NULL,
  `nok` varchar(40) NOT NULL,
  `nok_phone` varchar(16) NOT NULL,
  `medicare_no` varchar(12) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `case_hospitals` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `case_id` int NOT NULL,
  `hospital_id` int NOT NULL
);

CREATE TABLE IF NOT EXISTS `case_histories` (
  `case_id` int NOT NULL PRIMARY KEY,
  `pmhx` text NOT NULL,
  `meds` text NOT NULL,
  `anticoags` bool NOT NULL,
  `anticoags_last_dose` datetime NOT NULL,
  `hopc` text NOT NULL,
  `weight` float NOT NULL,
  `last_meal` datetime NOT NULL
);

CREATE TABLE IF NOT EXISTS `case_assessments` (
  `case_id` int NOT NULL PRIMARY KEY,
  `facial_droop` bool,
  `arm_drift` bool,
  `weak_grip` bool,
  `speech_difficulty` bool,
  `bp_systolic` int,
  `bp_diastolic` int,
  `heart_rate` int,
  `heart_rhythm` bool,
  `rr` int,
  `o2sats` int,
  `temp` int,
  `gcs` int,
  `blood_glucose` int,
  `facial_palsy_race` tinyint,
  `arm_motor_impair` tinyint,
  `leg_motor_impair` tinyint,
  `head_gaze_deviate` tinyint,
  `hemiparesis` bool,
  `cannula` bool,
  `conscious_level` tinyint,
  `month_age` tinyint,
  `blink_squeeze` tinyint,
  `horizontal_gaze` tinyint,
  `visual_fields` tinyint,
  `facial_palsy_nihss` tinyint,
  `left_arm_drift` tinyint,
  `right_arm_drift` tinyint,
  `left_leg_drift` tinyint,
  `right_leg_drift` tinyint,
  `limb_ataxia` tinyint,
  `sensation` tinyint,
  `aphasia` tinyint,
  `dysarthria` tinyint,
  `neglect` tinyint,
  `rankin_conscious` tinyint
);

CREATE TABLE IF NOT EXISTS `case_eds` (
  `case_id` int NOT NULL PRIMARY KEY,
  `location` VARCHAR(30) DEFAULT NULL,
  `registered` bool DEFAULT 0,
  `triaged` bool DEFAULT 0,
  `primary_survey` bool DEFAULT 0
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
  `large_vessel_occlusion` bool DEFAULT NULL
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
  `conservative_rx` bool DEFAULT NULL
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
