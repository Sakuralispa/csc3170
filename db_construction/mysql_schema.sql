-- 建库语句（请先在 SQLyog 或终端运行）
CREATE DATABASE IF NOT EXISTS college_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE college_db;

-- 舍监表
CREATE TABLE Warden (
    Warden_ID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(50),
    Phone VARCHAR(20),
    Hire_Date DATE
);

-- 楼栋表
CREATE TABLE Building (
    Building_ID VARCHAR(10) PRIMARY KEY,
    Floor_Count INT,
    Warden_ID VARCHAR(20),
    Location VARCHAR(100),
    FOREIGN KEY (Warden_ID) REFERENCES Warden(Warden_ID)
);

-- 宿舍表
CREATE TABLE Dorm (
    Dorm_ID VARCHAR(10) PRIMARY KEY,
    Dorm_Type ENUM('双人间', '四人间'),
    Max_Capacity INT,
    Air_Conditioner BOOLEAN,
    Fan BOOLEAN,
    Building_ID VARCHAR(10),
    FOREIGN KEY (Building_ID) REFERENCES Building(Building_ID)
);

-- 资产表
CREATE TABLE Asset (
    Asset_ID VARCHAR(20) PRIMARY KEY,
    Type ENUM('床', '床垫', '空调', '风扇', '桌子'),
    Status ENUM('正常', '报废', '检修中'),
    Purchase_Date DATE,
    Dorm_ID VARCHAR(10),
    Building_ID VARCHAR(10),
    FOREIGN KEY (Dorm_ID) REFERENCES Dorm(Dorm_ID),
    FOREIGN KEY (Building_ID) REFERENCES Building(Building_ID)
);

-- 导师表
CREATE TABLE Tutor (
    Tutor_ID VARCHAR(20) PRIMARY KEY,
    Assigned_Floor VARCHAR(20),
    Name VARCHAR(50) NOT NULL,
    Email VARCHAR(100),
    Office_Location VARCHAR(100),
    Warden_ID VARCHAR(20),
    FOREIGN KEY (Warden_ID) REFERENCES Warden(Warden_ID)
);

-- 活动表
CREATE TABLE Activity (
    Activity_ID VARCHAR(20) PRIMARY KEY,
    Title VARCHAR(100) NOT NULL,
    Time DATETIME,
    Location VARCHAR(100),
    Warden_ID VARCHAR(20),
    Capacity INT CHECK (Capacity >= 0),
    FOREIGN KEY (Warden_ID) REFERENCES Tutor(Tutor_ID)
);

-- 资产检修表
CREATE TABLE Asset_Maintenance (
    Maintenance_ID VARCHAR(20) PRIMARY KEY,
    Asset_ID VARCHAR(20),
    Date DATE,
    Technician VARCHAR(50),
    Result VARCHAR(200),
    Notes TEXT,
    FOREIGN KEY (Asset_ID) REFERENCES Asset(Asset_ID)
);

-- 学生表（最后建）
CREATE TABLE Student (
    Student_ID INT PRIMARY KEY,
    Name VARCHAR(50),
    Gender ENUM('M', 'F', 'O'),
    Enrollment_Year INT,
    Dorm_ID VARCHAR(10),
    Asset_ID VARCHAR(20),
    Phone VARCHAR(20),
    Status ENUM('在读', '休学', '毕业'),
    Tutor_ID VARCHAR(20),
    FOREIGN KEY (Dorm_ID) REFERENCES Dorm(Dorm_ID),
    FOREIGN KEY (Asset_ID) REFERENCES Asset(Asset_ID),
    FOREIGN KEY (Tutor_ID) REFERENCES Tutor(Tutor_ID),
    CONSTRAINT unique_bed_per_student UNIQUE (Asset_ID)
);

-- 创建sql触发器：确保资产检修日期不早于购买日期 
DELIMITER //
CREATE TRIGGER check_maintenance_date
BEFORE INSERT ON Asset_Maintenance
FOR EACH ROW
BEGIN
    DECLARE purchase_date DATE;
    
    SELECT Purchase_Date INTO purchase_date
    FROM Asset
    WHERE Asset_ID = NEW.Asset_ID;
    
    IF NEW.Date < purchase_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '检修日期不能早于资产购买日期';
    END IF;
END//
DELIMITER ;




-- 插入舍监数据
INSERT INTO Warden (Warden_ID, Name, Phone, Hire_Date) VALUES
('W001', '张老师', '13800001111', '2020-08-01'),
('W002', '李老师', '13800002222', '2021-03-15');

-- 插入楼栋数据
INSERT INTO Building (Building_ID, Floor_Count, Warden_ID, Location) VALUES
('B01', 5, 'W001', '南区A栋'),
('B02', 4, 'W002', '北区B栋');

-- 插入宿舍数据
INSERT INTO Dorm (Dorm_ID, Dorm_Type, Max_Capacity, Air_Conditioner, Fan, Building_ID) VALUES
('D101', '四人间', 4, TRUE, TRUE, 'B01'),
('D102', '双人间', 2, FALSE, TRUE, 'B01');

-- 插入资产数据
INSERT INTO Asset (Asset_ID, Type, Status, Purchase_Date, Dorm_ID, Building_ID) VALUES
('A001', '床', '正常', '2022-09-01', 'D101', 'B01'),
('A002', '空调', '检修中', '2021-06-15', 'D101', 'B01');

-- 插入导师数据
INSERT INTO Tutor (Tutor_ID, Assigned_Floor, Name, Email, Office_Location, Warden_ID) VALUES
('T001', '2F', '王博士', 'wang@univ.edu', '南区教学楼201', 'W001');

-- 插入活动数据
INSERT INTO Activity (Activity_ID, Title, Time, Location, Warden_ID, Capacity) VALUES
('ACT001', '消防演练', '2025-05-01 15:00:00', '南区操场', 'T001', 100);

-- 插入资产检修数据
INSERT INTO Asset_Maintenance (Maintenance_ID, Asset_ID, Date, Technician, Result, Notes) VALUES
('M001', 'A002', '2025-04-15', '维修工张三', '更换零件', '发现冷凝器故障');

-- 插入学生数据
INSERT INTO Student (Student_ID, Name, Gender, Enrollment_Year, Dorm_ID, Asset_ID, Phone, Status, Tutor_ID) VALUES
(20230001, '小明', 'M', 2023, 'D101', 'A001', '13900001111', '在读', 'T001');
