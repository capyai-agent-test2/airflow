Fix scheduler dag-version refresh to lock unfinished task instances by primary key in bounded batches, preventing deadlocks with concurrent task state updates from the api-server.
