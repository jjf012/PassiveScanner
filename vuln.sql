/*
Navicat MySQL Data Transfer

Source Server         : localhost
Source Server Version : 50718
Source Host           : 127.0.0.1:3306
Source Database       : wyproxy

Target Server Type    : MYSQL
Target Server Version : 50718
File Encoding         : 65001

Date: 2017-08-16 21:30:37
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for vuln
-- ----------------------------
DROP TABLE IF EXISTS `vuln`;
CREATE TABLE `vuln` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `host` varchar(255) DEFAULT NULL,
  `vuln_url` text,
  `vuln_param` varchar(255) DEFAULT NULL,
  `vuln_name` text,
  `scheme` char(10) DEFAULT NULL,
  `path` text,
  `default_inputs` text,
  `request_raw` mediumblob,
  `response_raw` mediumblob,
  `severity` varchar(255) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4;
SET FOREIGN_KEY_CHECKS=1;
