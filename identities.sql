CREATE DATABASE IF NOT EXISTS `codestroke$codestroke`;
USE `codestroke$codestroke`;


CREATE TABLE IF NOT EXISTS `id_gender` (
  `gender_id` tinyint NOT NULL PRIMARY KEY,
  `gender_str` varchar(1) NOT NULL
);

INSERT INTO id_gender
  (gender_id, gender_str)
VALUES
  (0, 'f'),
  (1, 'm'),
  (2, 'u');


CREATE TABLE IF NOT EXISTS `id_status` (
  `status_id` tinyint NOT NULL PRIMARY KEY,
  `status_str` varchar(20) NOT NULL
);

INSERT INTO id_status
  (status_id, status_str)
VALUES
  (0, 'incoming'),
  (1, 'active'),
  (2, 'completed');


CREATE TABLE IF NOT EXISTS `id_options` (
  `options_id` tinyint NOT NULL PRIMARY KEY,
  `options_str` varchar(20) NOT NULL
);

INSERT INTO id_options
  (options_id, options_str)
VALUES
  (0, 'no'),
  (1, 'yes'),
  (2, 'unknown');


CREATE TABLE IF NOT EXISTS `id_heart_rhythm` (
  `heart_rhythm_id` tinyint NOT NULL PRIMARY KEY,
  `heart_rhythm_str` varchar(20) NOT NULL
);

INSERT INTO id_heart_rhythm
  (heart_rhythm_id, heart_rhythm_str)
VALUES
  (0, 'regular'),
  (1, 'irregular');


CREATE TABLE IF NOT EXISTS `id_side` (
  `side_id` bool NOT NULL PRIMARY KEY,
  `side_str` varchar(5) NOT NULL
);

INSERT INTO id_side
  (side_id, side_str)
VALUES
  (0, 'none'),
  (1, 'left'),
  (2, 'right');
