INSERT INTO users (username, prof_img_url, is_admin, is_activated) VALUES (
    'paul',
    'https://play-lh.googleusercontent.com/Vc7Ud-kgiUrAqRY59RrXOBP6TNfDcCA6wATgnIGFMORbJa1NZnj9n9Bhr-SQnemLiw',
    true,
    true
);

-- paul is auto activated. Chuck the password straight in
INSERT INTO auth (username, hashpsw) VALUES ('paul', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08iamateapotshortandstout');

INSERT INTO users (username) VALUES ('james');
INSERT INTO users (username) VALUES ('leo');
INSERT INTO users (username) VALUES ('anna');
INSERT INTO users (username) VALUES ('sven');
INSERT INTO users (username) VALUES ('jack');
INSERT INTO users (username) VALUES ('blake');
INSERT INTO users (username) VALUES ('haydn');
INSERT INTO users (username) VALUES ('jason');