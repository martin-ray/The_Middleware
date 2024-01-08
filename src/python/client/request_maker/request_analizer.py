from request_maker import requestMaker
from collections import Counter

def recycle_counter(reqs):
    sequece_len = len(reqs)
    accessed_blocks = Counter(reqs) 
    num_of_accessed_blocks = len(accessed_blocks)
    num_of_recycle_access = sequece_len - num_of_accessed_blocks
    return num_of_recycle_access
    
def max_distance_calculator(reqs):

    max_distance = 0
    # Iterate through the list to find the maximum distance
    for i in range(len(reqs)):
        for j in range(i + 1, len(reqs)):
            # Extract the x, y, and z values from each element (ignoring the first value)
            t1, x1, y1, z1 = reqs[i][1], reqs[i][2], reqs[i][3], reqs[i][4]
            t2, x2, y2, z2 = reqs[j][1], reqs[j][2], reqs[j][3], reqs[j][4]
            
            # Check if the digits are divisible by 256
            if x1 % 256 == 0 and x2 % 256 == 0 and y1 % 256 == 0 and y2 % 256 == 0 and z1 % 256 == 0 and z2 % 256 == 0:
                # Calculate the Chebyshev distance
                spatial_distance = max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2)) / 256
                temporal_distance = abs(t1 - t2)
                distance = spatial_distance + temporal_distance
                # Update the maximum distance if the current distance is greater
                if distance > max_distance:
                    max_distance = distance

    return max_distance

def request_analiser(reqs):
    num_request = len(reqs)

    num_of_recycle_access = recycle_counter(reqs)
    recycle_ratio = num_of_recycle_access/num_request

    max_distance = max_distance_calculator(reqs)
    access_density = 1- max_distance/num_request

    return {"recycle_ratio":recycle_ratio,
            "maxDistance":max_distance,
            "access_density":access_density}



if __name__ == "__main__":    
    blockSize = 256
    maxtimestep=63
    num_request = 64
    randomRatio = 0

    reqMaker = requestMaker(blockSize,maxtimestep)
    reqs = reqMaker.randAndcontMixRequester(num_request,randomRatio)

    num_of_recycle_access = recycle_counter(reqs)
    recycle_ratio = num_of_recycle_access/num_request

    max_distance = max_distance_calculator(reqs)
    access_dencity = 1- max_distance/num_request

    print(f"num_requests={num_request}\n\
        num_of_recycle_access={num_of_recycle_access} \
        recycle_ratio={recycle_ratio}\n \
            max__distance={max_distance} \
            access_dencity={access_dencity} \
            ")

