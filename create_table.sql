CREATE TABLE block (
  id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  created TIMESTAMP,
  time TIMESTAMP,
  height int(11),
  hash varchar(64)
);


CREATE TABLE block_info (
  id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  created TIMESTAMP,
  time TIMESTAMP, 
  height int(11),
  hash varchar(64),
  metric VARCHAR(255) NOT NULL,
  value float
);
