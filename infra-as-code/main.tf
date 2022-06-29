
data "aws_region" "current_region" {}

locals {
  PROJECT_NAME                 = "iot-processing"
  ENV                          = "dev"
  AWS_REGION                   = data.aws_region.current_region.name
  NUMBER_OF_KDS_SHARDS         = 1
}

#lambda region
module "lambda-event-producer" {
  source          = "./modules/lambda"
  ENV             = local.ENV
  PROJECT_NAME    = local.PROJECT_NAME
  RESOURCE_SUFFIX = "random-data-generator"
  LAMBDA_SETTINGS = {
    "description"         = "This function is a data producer that emulates up to NUMBER_THREADS IoT Devices"
    "handler"             = "producer.lambda_handler"
    "runtime"             = "python3.8"
    "timeout"             = 900
    "memory_size"         = 512
    "lambda_script_folder"  = "../lambdas/"
  }
  LAMBDA_ENVIRONMENT_VARIABLES = {
    "KDS_PARTITIONS"      = local.NUMBER_OF_KDS_SHARDS
    "CSV_PATH_LOCATION"   = "clients_annual_income.csv"
    "KDS_NAME"            = module.kds-ingestion.name
    "NUMBER_OF_THREADS"   = 10
    "REGION"              = local.AWS_REGION
  }
}
#endregion

#region KDS
module "kds-ingestion" {
  source            = "./modules/kinesis-data-stream"
  ENV               = local.ENV
  PROJECT_NAME      = local.PROJECT_NAME
  RESOURCE_SUFFIX   = "ingestion-stream"
  NUMBER_OF_SHARDS  = local.NUMBER_OF_KDS_SHARDS
}#end region