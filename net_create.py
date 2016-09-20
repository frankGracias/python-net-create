import boto3
import os
import sys

### User Configuration 
# - Credentials
ACCESS_KEY = ''
ACCESS_SECRET = ''
REGION_NAME = ''
PROFILE = ''

#######################


os.system('clear')
#Client Object
ec2_client = boto3.client(
                             'ec2',
                             aws_access_key_id= ACCESS_KEY,
                             aws_secret_access_key= ACCESS_SECRET,
                             profile_name = PROFILE
                         )



 #Get the CIDR for the new VPC
 VPC_CIDR = raw_input("Type CIDR block to use, Press 'Enter' when finished : ")

 #Get the tag for the new VPC
 VPC_TAG = raw_input("Type the Name for VPC (to use as Tag), Press 'Enter' when finished : ")


 #Check if VPC is present, if not, create it. 
 print ''
 print '[INFO] Checking if VPC is present ..'

 vpc_present = ec2_client.describe_vpcs(Filters = [{ 'Name' : 'cidr', 'Values' : [VPC_CIDR]}])

 if len(vpc_present[u'Vpcs']) > 0 :
     print '[ERROR] VPC with CIDR ' + VPC_CIDR + ' already exists. Terminating the script '
     sys.exit()
 else:
     print '[INFO] Creating a new VPC with CIDR ' + VPC_CIDR + ' and name tag as ' + VPC_TAG
     try : 
         response = ec2_client.create_vpc(CidrBlock= VPC_CIDR)
         VPC_ID = response[u'Vpc'][u'VpcId']
         ec2_client.create_tags(Resources = [VPC_ID], Tags = [{'Key' : 'Name', 'Value' : VPC_TAG}])
      
     except:
         print("[ERROR] Unable to create the VPC",sys.exc_info()[0])
         sys.exit()    

 #Create Internet Gateway and attach it to the newly created VPC
 print ''
 print '[INFO] Creating a Internet Gateway'
 try :
     gateway_obj = ec2_client.create_internet_gateway()
     gateway_id = gateway_obj[u'InternetGateway'][u'InternetGatewayId']
     print '[INFO] Attaching the Internet Gateway ' + gateway_id + ' to the VPC ' + VPC_ID
     ec2_client.attach_internet_gateway(InternetGatewayId = gateway_id , VpcId = VPC_ID)
     ec2_client.create_tags(Resources = [gateway_id], Tags = [{'Key' : 'Name', 'Value' : 'VPC_GATEWAY '+ gateway_id}, {'Key' : 'VPC_ID', 'Value' : VPC_ID}])
 except:
     print("[ERROR] Unable to create the Internet Gateway",sys.exc_info()[0])

 #Create Route Table 
 print ''
 print '[INFO] Creating a Route Table'
 try :
     route_table_obj = ec2_client.create_route_table(VpcId = VPC_ID)
     route_table_id = route_table_obj[u'RouteTable'][u'RouteTableId']
     ec2_client.create_tags(Resources = [route_table_id], Tags = [{'Key' : 'Name', 'Value' : 'ROUTE_TABLE'}, {'Key' : 'VPC_ID', 'Value' : VPC_ID}])
     print "[INFO] Route table created for VPC - " + VPC_ID
 except:
     print("[ERROR] Unable to create the Route Table",sys.exc_info()[0])

 #Creating a Subnet
 print ''
 print '[INFO] Creating new Subnets '
 no_of_subnets = raw_input(" - Enter the number of Subnets to be created : ")
 for i in range(1,int(no_of_subnets) +1) :
     try:
         subnet_cidr = raw_input(" - Enter the CIDR Block for subnet " + str(i)+ ' : ')
         subnet_tag = raw_input(" - Enter the Name tag for subnet " + str(i)+ ' : ')
         subnet_response = ec2_client.create_subnet(VpcId = VPC_ID, CidrBlock = subnet_cidr, AvailabilityZone = 'us-east-1a' ) 
         subnet_id = subnet_response[u'Subnet'][u'SubnetId']  
         ec2_client.create_tags(Resources = [subnet_id], Tags = [{'Key' : 'Name', 'Value' : subnet_tag}, {'Key' : 'VPC_ID', 'Value' : VPC_ID}])
         print "[INFO] Created subnet with with CIDR " + subnet_cidr + ' and tag ' + subnet_tag
         #Associate Subnet with Route Table
         associate_subnet = raw_input(" - Associate subnet to route table " + route_table_id + " [y/n] : ")
         if associate_subnet == 'y' :
             route_table = ec2_client.associate_route_table(SubnetId = subnet_id, RouteTableId = route_table_id)

     except:
         print("[ERROR] Unable to create the Route Table",sys.exc_info())     




# #Create Route 
 print ''
 print '[INFO] Creating a Route from the Internet Gateway ' + gateway_id + ' with route table ' + route_table_id
 ec2_client.create_route(RouteTableId= route_table_id, DestinationCidrBlock= '0.0.0.0/0', GatewayId= gateway_id)



 #Create Security group for the subnet
 print ''
 print '[INFO] Creating Security Groups associated to the VPC - ' + VPC_ID
 no_of_secgrps = raw_input(" - Enter the number of security groups to be created : ")
 for i in range(1,int(no_of_secgrps) +1) :
     print ''
     grp_name = raw_input(" - Enter the Group Name for security group " + str(i) + " : ")
     grp_description = raw_input(" - Enter the Group Description for security group " + str(i) + " : ")
     security_grp = ec2_client.create_security_group(GroupName = grp_name, Description = grp_description, VpcId = VPC_ID)
     print '[INFO] Security Group Created - ' + security_grp['GroupId']
  
     #Authorize Egress Traffic
     authorize_traffic = raw_input(" - Add security group rules - EGRESS  [y/n] : ")
     if authorize_traffic == 'y' :
         authorize_egress = 'y'
         while authorize_egress == 'y' :
             authorize_egress = raw_input(" - Add security group rule for a specific protocol ? [y/n] : ")
             if authorize_egress == 'y' :
                 get_auth_string = raw_input(" - Enter the rule string (protocol from_port to_port cidr) : ")
                 protocol_str = get_auth_string.split(" ")[0]
                 from_port_str = int(get_auth_string.split(" ")[1])
                 to_port_str = int(get_auth_string.split(" ")[2])
                 cidr_str = get_auth_string.split(" ")[3]                
                 # ec2_client.authorize_security_group_egress(GroupId= security_grp['GroupId'], IpProtocol=protocol_str, FromPort=from_port_str, ToPort=to_port_str, CidrIp=cidr_str)
                 ec2_client.authorize_security_group_egress(
                                                                 GroupId= security_grp['GroupId'],
                                                                 IpPermissions = [
                                                                     {
                                                                         'IpProtocol' : protocol_str,
                                                                         'FromPort' : from_port_str,
                                                                         'ToPort' : to_port_str,
                                                                         'IpRanges' : [{'CidrIp': cidr_str}]
                                                                     }
                                                                 ]
                 )     
      
 #Creating Network ACL 
 print ''
 print '[INFO] Creating Network ACL associated with VPC - ' + VPC_ID
 try:
     network_acl = ec2_client.create_network_acl(VpcId = VPC_ID)
     network_acl_id = network_acl['NetworkAcl']['NetworkAclId']
     ec2_client.create_tags(Resources = [network_acl_id], Tags = [{'Key' : 'Name', 'Value' : 'Network ACL'}, {'Key' : 'VPC_ID', 'Value' : VPC_ID}])
     print '[INFO] Network ACL ' + network_acl_id + ' Created '
 except:
     print '[ERROR] Unable to create a Network ACL'

#VPC_ID = 'vpc-e0f6ae87'






print ''
###################################
#Fetch All Associations for the VPC 
###################################

# Fetch All Subnets
all_subnets = ec2_client.describe_subnets(Filters = [{ 'Name' : 'vpc-id', 'Values' : [VPC_ID]}])
print '[INFO] Fetching all associated subnets for VPC - ' + VPC_ID
if len(all_subnets['Subnets']) > 0 :
    for i in all_subnets['Subnets'] : 
        print ' - Subnet : ' + i['SubnetId']
else:
    print ' - No Subnet found for VPC - ' + VPC_ID


# Fetch All Security Groups 
print ''
all_sec_grps = ec2_client.describe_security_groups(Filters = [{ 'Name' : 'vpc-id', 'Values' : [VPC_ID]}])
print '[INFO] Fetching all associated security groups for VPC - ' + VPC_ID
if len(all_sec_grps['SecurityGroups']) > 0 :
    for i in all_sec_grps['SecurityGroups'] : 
        print ' - Security Group : ' + i['GroupId']
else:
    print ' - No Security Group found for VPC - ' + VPC_ID


# Fetch All Network ACLs
print ''
all_net_acl = ec2_client.describe_network_acls(Filters = [{ 'Name' : 'vpc-id', 'Values' : [VPC_ID]}])
print '[INFO] Fetching all associated network acls for VPC - ' + VPC_ID
if len(all_net_acl['NetworkAcls']) > 0 :
    for i in all_net_acl['NetworkAcls'] : 
        print ' - Network ACL : ' + i['NetworkAclId']
else:
    print ' - No Network ACL found for VPC - ' + VPC_ID


# Fetch All Internet Gateways
print ''
all_int_gateway = ec2_client.describe_internet_gateways(Filters = [{ 'Name' : 'attachment.vpc-id', 'Values' : [VPC_ID]}])
print '[INFO] Fetching all associated internet gateway for VPC - ' + VPC_ID
if len(all_int_gateway['InternetGateways']) > 0 :
    for i in all_int_gateway['InternetGateways'] : 
        print ' - Internet Gateway : ' + i['InternetGatewayId']
else:
    print ' - No Internet Gateway found for VPC - ' + VPC_ID


# Fetch All Route Tables
print ''
all_route_tables = ec2_client.describe_route_tables(Filters = [{ 'Name' : 'vpc-id', 'Values' : [VPC_ID]}])
print '[INFO] Fetching all associated route tables for VPC - ' + VPC_ID
if len(all_route_tables['RouteTables']) > 0 :
    for i in all_route_tables['RouteTables'] : 
        print ' - Route Table : ' + i['RouteTableId']
else:
    print ' - No Route Table found for VPC - ' + VPC_ID













print ''
print ''






