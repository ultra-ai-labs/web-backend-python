-- Drop UNIQUE constraints on email and username to allow optional fields
ALTER TABLE `users` DROP INDEX `email`;
ALTER TABLE `users` DROP INDEX `username`;
