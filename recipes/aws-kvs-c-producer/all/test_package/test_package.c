#include <stdio.h>
#ifdef TEST_COMMON_CURL
#include <com/amazonaws/kinesis/video/cproducer/Include.h>
#endif

#ifdef TEST_COMMON_LWS
#include <com/amazonaws/kinesis/video/common/Include.h>
#endif

int main() {

#ifdef TEST_COMMON_CURL
    printf("Testing producer.. \n");
    PStreamInfo pStreamInfo = NULL;
    PCHAR streamName = "Conan";
    createRealtimeVideoStreamInfoProvider(streamName, 2 * HUNDREDS_OF_NANOS_IN_AN_HOUR, 120 * HUNDREDS_OF_NANOS_IN_A_SECOND, &pStreamInfo);
#endif

#ifdef TEST_COMMON_LWS
    printf("Testing common_lws.. \n");
    PCHAR iotGetCredentialEndpoint = NULL;
    PCHAR certPath = NULL;
    PCHAR privateKeyPath = NULL;
    PCHAR caCertPath = NULL;
    PCHAR roleAlias = NULL;
    PCHAR thingName = NULL;
    PAwsCredentialProvider* ppCredentialProvider;
    createLwsIotCredentialProvider(iotGetCredentialEndpoint, certPath, privateKeyPath, caCertPath, roleAlias, thingName, ppCredentialProvider);
#endif
    printf("Done. \n");
    return 0;
}
