CREATE DATABASE IF NOT EXISTS `codestroke`
USE `codestroke`;

CREATE TABLE IF NOT EXISTS `cases` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `dob` date NOT NULL,
  `address` text NOT NULL,
  `gender` varchar(1) NOT NULL,
  `last_well` datetime NOT NULL,
  `nok` varchar(40) NOT NULL,
  `nok_phone` varchar(16) NOT NULL,
  `medicare_no` varchar(12) DEFAULT NULL,
);

CREATE TABLE IF NOT EXISTS `case_hospital` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `case_id` int NOT NULL,
  `hospital_id` int NOT NULL,
);

CREATE TABLE IF NOT EXISTS `historys` (
  `case_id` int NOT NULL PRIMARY KEY,
  `pmhx` text NOT NULL,
  `meds` text NOT NULL,
  `anticoags` bit(1) NOT NULL,
  `anticoags_last_dose` datetime NOT NULL,
  `hopc` text NOT NULL,
  `weight` float NOT NULL,
  `last_meal` datetime NOT NULL,
);

CREATE TABLE IF NOT EXISTS `assessments` (
  `case_id` int NOT NULL PRIMARY KEY,
  `facial_droop` bit(1),
  `arm_drift` bit(1),
  `weak_grip` bit(1),
  `speech_difficulty` bit(1),
  `bp_systolic` int,
  `bp_diastolic` int,
  `heart_rate` int,
  `heart_rhythm` bit(1),
  `rr` int,
  `o2sats` int,
  `temp` int,
  `gcs` int,
  `blood_glucose` int,
  `facial_palsy` tinyint,
  `arm_motor_impair` tinyint,
  `leg_motor_impair` tinyint,
  `head_gaze_deviate` tinyint,
  `hemiparesis` bit(1),
  `cannula` bit(1),
  `conscious_level` tinyint,
  `month_age` tinyint,
  `blink_squeeze` tinyint,
  `horizontal_gaze` tinyint,
  `visual_fields` tinyint,
  `facial_palsy` tinyint,
  `left_arm_drift` tinyint,
  `right_arm_drift` tinyint,
  `left_leg_drift` tinyint,
  `right_leg_drift` tinyint,
  `limb_ataxia` tinyint,
  `sensation` tinyint,
  `aphasia` tinyint,
  `dysarthria` tinyint,
  `neglect` tinyint,
  `rankin_conscious` tinyint,
);

CREATE TABLE IF NOT EXISTS `ed` (
  `case_id` int NOT NULL PRIMARY KEY,
  `location` VARCHAR(30) DEFAULT NULL,
  `registered` bit(1) DEFAULT 0,
  `triaged` bit(1) DEFAULT 0,
  `primary_survey` bit(1) DEFAULT 0,
);

CREATE TABLE IF NOT EXISTS `radiology` (
  `case_id` int NOT NULL PRIMARY KEY,
  `ct1` bit(1) DEFAULT 0,
  `ct2` bit(1) DEFAULT 0,
  `ct3` bit(1) DEFAULT 0,
  `arrived_to_ct` bit(1) DEFAULT 0,
  `ct_complete` bit(1) DEFAULT 0,
  `ich_found` bit(1) DEFAULT NULL,
  `do_cta_ctp` bit(1) DEFAULT NULL,
  `cta_ctp_complete` bit(1) DEFAULT 0,
  `large_vessel_occlusion` bit(1) DEFAULT NULL,
);

CREATE TABLE IF NOT EXISTS `management` (
  `case_id` int NOT NULL PRIMARY KEY,
  `thrombolysis` bit(1) DEFAULT NULL,
  `new_trauma_haemorrhage` bit(1) DEFAULT NULL,
  `uncontrolled_htn` bit(1) DEFAULT NULL,
  `history_ich` bit(1) DEFAULT NULL,
  `known_intracranial` bit(1) DEFAULT NULL,
  `active_bleed` bit(1) DEFAULT NULL,
  `endocarditis` bit(1) DEFAULT NULL,
  `bleeding_diathesis` bit(1) DEFAULT NULL,
  `abnormal_blood_glucose` bit(1) DEFAULT NULL,
  `rapidly_improving` bit(1) DEFAULT NULL,
  `recent_trauma_surgery` bit(1) DEFAULT NULL,
  `recent_active_bleed` bit(1) DEFAULT NULL,
  `seizure_onset` bit(1) DEFAULT NULL,
  `recent_arterial_puncture` bit(1) DEFAULT NULL,
  `recent_lumbar_puncture` bit(1) DEFAULT NULL,
  `post_acs_pericarditis` bit(1) DEFAULT NULL,
  `pregnant` bit(1) DEFAULT NULL,
  `thrombolysis_time_given` datetime DEFAULT NULL,
  `ecr` DEFAULT NULL,
  `surgical_rx` DEFAULT NULL,
  `conservative_rx` DEFAULT NULL,
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
  `email` varchar(40),
);

CREATE TABLE IF NOT EXISTS `hospitals` (
  `id` int NOT NULL PRIMARY KEY,
  `name` varchar(30) NOT NULL,
  `city` varchar(30),
  `state` varchar(5),
  `postcode` varchar(30),
  `latitude` text,
  `longitude` text,
);
