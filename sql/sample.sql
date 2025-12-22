INSERT INTO users (username, prof_img_url, is_admin, is_activated) VALUES (
    'peclarke',
    'https://play-lh.googleusercontent.com/Vc7Ud-kgiUrAqRY59RrXOBP6TNfDcCA6wATgnIGFMORbJa1NZnj9n9Bhr-SQnemLiw',
    true,
    true
);

-- password is test
INSERT INTO auth (username, hashpsw) VALUES ('peclarke', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08iamateapotshortandstout');

INSERT INTO users (username) VALUES ('jimmyd');
INSERT INTO users (username) VALUES ('brimblecombel');

-- INSERT INTO bingo DEFAULT VALUES;