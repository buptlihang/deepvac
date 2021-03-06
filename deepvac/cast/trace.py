from ..utils import LOG
from .base import DeepvacCast, FXQuantizeAndTrace

class TraceCast(DeepvacCast):
    def __init__(self, deepvac_train_config):
        super(TraceCast,self).__init__(deepvac_train_config)

    def auditConfig(self):
        if not self.config.trace_model_dir:
            return False

        if not self.config.static_quantize_dir:
            return True
            
        if self.config.is_forward_only and self.config.test_loader is None:
            LOG.logE("You must set config.train.test_loader in config.py when config.train.static_quantize_dir is enabled.", exit=True)
        if not self.config.is_forward_only and self.config.val_loader is None:
            LOG.logE("You must set config.train.val_loader in config.py when config.train.static_quantize_dir is enabled.", exit=True)

        return True

    def process(self, cast_output_file=None):
        output_trace_file = self.config.trace_model_dir
        if cast_output_file:
            output_trace_file = '{}/trace_{}.pt'.format(self.config.output_dir, cast_output_file)

        LOG.logI("config.trace_model_dir found, save trace model to {}...".format(output_trace_file))
        trace_model = FXQuantizeAndTrace(self.config, output_trace_file)
        trace_model.save()

        if self.config.dynamic_quantize_dir:
            LOG.logI("You have enabled config.dynamic_quantize_dir, will dynamic quantize the model...")
            trace_model.saveDQ()

        if self.config.static_quantize_dir:
            LOG.logI("You have enabled config.static_quantize_dir, will static quantize the model...")
            trace_model.saveSQ()