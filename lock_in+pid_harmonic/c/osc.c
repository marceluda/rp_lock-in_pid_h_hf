#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>

#include <errno.h>


#include <unistd.h>
//#include <signal.h>



#define PARAMS_NUM 20


#define OSC_FPGA_BASE_ADDR 0x40100000
#define OSC_FPGA_BASE_SIZE 0x30000



/* Registers description structure */
typedef struct registers_s {
    char  *name;
    int    index;
    int    is_signed;
    int    read_only;
    float  min_val;
    float  max_val;
} registers_t;



static registers_t registers[PARAMS_NUM] = {
    { "conf"                   ,   0, 0, 0,      -8192,       8192 },
    { "TrgSrc"                 ,   1, 0, 0,      -8192,       8192 },
    { "ChAth"                  ,   2, 1, 0,      -8192,       8192 },
    { "ChBth"                  ,   3, 1, 0,      -8192,       8192 },
    { "TrgDelay"               ,   4, 0, 0,          0,      16383 },
    { "Dec"                    ,   5, 0, 0,          0,      32767 },
    { "CurWpt"                 ,   6, 0, 0,          0,      16383 },
    { "TrgWpt"                 ,   7, 0, 0,          0,      16383 },
    { "ChAHys"                 ,   8, 0, 0,      -8192,       8192 },
    { "ChBHys"                 ,   9, 0, 0,      -8192,       8192 },
    { "AvgEn"                  ,  10, 0, 0,      -8192,       8192 },
    { "PreTrgCnt"              ,  11, 0, 0,      -8192,       8192 },
    { "ChAEqFil1"              ,  12, 0, 0,      -8192,       8192 },
    { "ChAEqFil2"              ,  13, 0, 0,      -8192,       8192 },
    { "ChAEqFil3"              ,  14, 0, 0,      -8192,       8192 },
    { "ChAEqFil4"              ,  15, 0, 0,      -8192,       8192 },
    { "ChBEqFil1"              ,  16, 0, 0,      -8192,       8192 },
    { "ChBEqFil2"              ,  17, 0, 0,      -8192,       8192 },
    { "ChBEqFil3"              ,  18, 0, 0,      -8192,       8192 },
    { "ChBEqFil4"              ,  19, 0, 0,      -8192,       8192 }
};



// Function for string to int conversion **********************************
typedef enum {
    STR2INT_SUCCESS,
    STR2INT_OVERFLOW,
    STR2INT_UNDERFLOW,
    STR2INT_INCONVERTIBLE
} str2int_errno;

/* Convert string s to int out.
 *
 * @param[out] out The converted int. Cannot be NULL.
 *
 * @param[in] s Input string to be converted.
 *
 *     The format is the same as strtol,
 *     except that the following are inconvertible:
 *
 *     - empty string
 *     - leading whitespace
 *     - any trailing characters that are not part of the number
 *
 *     Cannot be NULL.
 *
 * @param[in] base Base to interpret string in. Same range as strtol (2 to 36).
 *
 * @return Indicates if the operation succeeded, or why it failed.
 */
str2int_errno str2int(int32_t *out, char *s, int base) {
    char *end;
    if (s[0] == '\0' || isspace(s[0]))
        return STR2INT_INCONVERTIBLE;
    errno = 0;
    long l = strtol(s, &end, base);
    /* Both checks are needed because INT_MAX == LONG_MAX is possible. */
    if (l > INT_MAX || (errno == ERANGE && l == LONG_MAX))
        return STR2INT_OVERFLOW;
    if (l < INT_MIN || (errno == ERANGE && l == LONG_MIN))
        return STR2INT_UNDERFLOW;
    if (*end != '\0')
        return STR2INT_INCONVERTIBLE;
    *out = l;
    return STR2INT_SUCCESS;
}


//***************************************************************************


// For memory reading
char      *name = "/dev/mem";
int        fd;
void      *osc_ptr ;
int32_t   *osc ;




/* Reading FPGA register of Oscilloscope module
 *
 * @param[index] number of the register
 *
 * @return Returns the register value
 *
 **/
void read_reg(int index){
    printf("%s:%d\n" , registers[index].name , osc[index] );
}


/* Write FPGA register value of Oscilloscope module
 *
 * @param[index] number of the register
 *
 * @param[val] value to be written
 *
 * @return Returns the register value
 *
 **/
void write_reg(int index, int32_t val ){
    osc[index] = val ;
    printf("%s:%d\n" , registers[index].name , osc[index] );
}



/* Get index number from parameter name
 *
 * @param[name] name of the parameter
*
 * @return Returns the register index
 *
 **/
int reg_name_to_index(char *name){
    for(int jj=0; jj<PARAMS_NUM ; jj++){
        if (strcmp(name, registers[jj].name ) == 0) return registers[jj].index ;
    }
    return -1 ;
}





int main(int argc, char *argv[]) {
    int32_t  s_value=0 ;
    uint32_t u_value=0 ;
    int jj=0 ;
    int index;



    // Open Linux memory device


    if((fd = open(name, O_RDWR)) < 0) {
        perror("[-] Error trying to open /dev/mem");
        return 1;
    }

    // Pointer for oscilloscope block memory addreses
    long osc_size = sysconf(_SC_PAGESIZE);
    long osc_addr = OSC_FPGA_BASE_ADDR & (~(osc_size-1));
    long osc_off  = OSC_FPGA_BASE_ADDR - osc_addr;

    //        *mmap(*addr,             length,       prot            , flags     , fd ,  offset  );
    osc_ptr = mmap(NULL, OSC_FPGA_BASE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd , osc_addr);

    if((void *)osc_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] osc mmap() failed: %d\n", errno);
        return -1;
    }

    osc       = osc_ptr ;


    if(argc>1){
        // Arguments arte the reg names and values te be read and written
        for(jj=1; jj<argc ; jj++){

            index = reg_name_to_index(argv[jj]);

            if( index<0 ){
                fprintf(stdout,"ERROR: parameter '%s' not found\n", argv[jj]);
                return -1 ;
            }

            if( (jj+1<argc) &&  (str2int(&s_value, argv[jj+1], 10)==STR2INT_SUCCESS)   ){
                // Next arg is a number. Must be a write operation

                if(registers[index].read_only) {
                    printf("ERROR: %s is read-only and cannot be written\n",registers[index].name );
                    return -2;
                }
                if( (!registers[index].is_signed) && (s_value<0) ) {
                    printf("ERROR: %s is not a signed register and you tried to sed value %d\n",registers[index].name, s_value );
                    return -2;
                }
                write_reg(index, s_value);

                jj++; // skip value
            }else{
                // There's no next or it's not a number. Must be a read operation
                read_reg(index);
            }
        }
    }else{
        // Just print all the values
        for(jj=0; jj<PARAMS_NUM ; jj++){
            read_reg(jj);
            //printf("%d\n" , osc[jj] );
        }
    }

    // Clean the osc_ptr pointer
    munmap(osc_ptr, sysconf(_SC_PAGESIZE));
    return EXIT_SUCCESS;
}