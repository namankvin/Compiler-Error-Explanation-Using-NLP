// Test Case S3: Buffer Overflow with strcpy
// Expected Error: warning about potential buffer overflow
// Student Error Pattern: Using unsafe string functions
// Difficulty: Intermediate

#include <stdio.h>
#include <string.h>

int main() {
    char small_buffer[10];
    char *long_string = "This is a very long string that will overflow";
    
    // Dangerous: no bounds checking
    strcpy(small_buffer, long_string);
    
    printf("Buffer contains: %s\n", small_buffer);
    return 0;
}
