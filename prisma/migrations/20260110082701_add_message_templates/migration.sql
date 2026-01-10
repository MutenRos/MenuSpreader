-- CreateTable
CREATE TABLE "MessageTemplate" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "barId" TEXT NOT NULL,
    CONSTRAINT "MessageTemplate_barId_fkey" FOREIGN KEY ("barId") REFERENCES "Bar" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
